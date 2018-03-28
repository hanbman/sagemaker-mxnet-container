import logging
import os
import platform

import boto3
import pytest
import shutil
import tempfile

from sagemaker import Session

logger = logging.getLogger(__name__)
logging.getLogger('boto').setLevel(logging.INFO)
logging.getLogger('botocore').setLevel(logging.INFO)
logging.getLogger('factory.py').setLevel(logging.INFO)
logging.getLogger('auth.py').setLevel(logging.INFO)
logging.getLogger('connectionpool.py').setLevel(logging.INFO)

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


def pytest_addoption(parser):
    parser.addoption('--docker-base-name', default='preprod-mxnet')
    parser.addoption('--region', default='us-west-2')
    parser.addoption('--framework-version', required=True)
    parser.addoption('--py-version', required=True, choices=['2', '3'])
    parser.addoption('--processor', required=True, choices=['gpu','cpu'])
    # If not specified, will default to {framework-version}-{processor}-py{py-version}
    parser.addoption('--tag', default=None)

@pytest.fixture(scope='session')
def docker_base_name(request):
    return request.config.getoption('--docker-base-name')


@pytest.fixture(scope='session')
def region(request):
    return request.config.getoption('--region')


@pytest.fixture(scope='session')
def framework_version(request):
    return request.config.getoption('--framework-version')


@pytest.fixture(scope='session')
def py_version(request):
    return int(request.config.getoption('--py-version'))


@pytest.fixture(scope='session')
def processor(request):
    return request.config.getoption('--processor')


@pytest.fixture(scope='session')
def tag(request, framework_version, processor, py_version):
    provided_tag = request.config.getoption('--tag')
    default_tag = '{}-{}-py{}'.format(framework_version, processor, py_version)
    return provided_tag if provided_tag is not None else default_tag


@pytest.fixture(scope='session')
def docker_image(docker_base_name, tag):
    return '{}:{}'.format(docker_base_name, tag)


@pytest.fixture(scope='session')
def sagemaker_session(region):
    return Session(boto_session=boto3.Session(region_name=region))


@pytest.fixture
def opt_ml():
    tmp = tempfile.mkdtemp()
    os.mkdir(os.path.join(tmp, 'output'))

    # Docker cannot mount Mac OS /var folder properly see
    # https://forums.docker.com/t/var-folders-isnt-mounted-properly/9600
    opt_ml_dir = '/private{}'.format(tmp) if platform.system() == 'Darwin' else tmp
    yield opt_ml_dir

    shutil.rmtree(tmp, True)