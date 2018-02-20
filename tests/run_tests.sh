#!/bin/bash
# This script is meant to be called by the "script" step defined in
# .travis.yml. See http://docs.travis-ci.com/ for more details.
# The behavior of the script is controlled by environment variabled defined in the .travis.yml in the top level folder of the project.

set -e

# Environment Version Information
python --version
python -c "import numpy; print('numpy %s' % numpy.__version__)"
python -c "import scipy; print('scipy %s' % scipy.__version__)"

conda list
conda env list


run_tests() {
    TEST_CMD="pytest --showlocals --durations=20 --pyargs"

    # Get into a temp directory to run test from the installed scikit-learn and
    # check if we do not leave artifacts
    mkdir -p $TEST_DIR
    # We need the setup.cfg for the pytest settings
    cp setup.cfg $TEST_DIR
    cd $TEST_DIR

    # Skip tests that require large downloads over the network to save bandwidth
    # usage as travis workers are stateless and therefore traditional local
    # disk caching does not work.
    export SKIP_NETWORK_TESTS=1

    if [[ "$COVERAGE" == "true" ]]; then
        TEST_CMD="$TEST_CMD --cov aichat"
    fi
    $TEST_CMD sklearn

    # Going back to git checkout folder needed to test documentation
    cd $OLDPWD

    make test-doc
}

if [[ "$RUN_FLAKE8" == "true" ]]; then
    source tests/flake8_diff.sh
fi

if [[ "$SKIP_TESTS" != "true" ]]; then
    run_tests
fi

if [[ "$CHECK_PYTEST_SOFT_DEPENDENCY" == "true" ]]; then
    conda remove -y py pytest || pip uninstall -y py pytest
    if [[ "$COVERAGE" == "true" ]]; then
        # Need to append the coverage to the existing .coverage generated by
        # running the tests
        CMD="coverage run --append"
    else
        CMD="python"
    fi
    # .coverage from running the tests is in TEST_DIR
    cd $TEST_DIR
    $CMD -m sklearn.utils.tests.test_estimator_checks
    cd $OLDPWD
fi