import os
import csv
import pytest
from os import path
import pandas as pd
from io import StringIO
from mock import mock_open, patch
from src.vector_db.aws_database_auth import connection_string


@pytest.fixture
def mock_pandas_read_csv(mocker):
    db_file_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "database-info.csv")
    read_data = 'dbname,user,password,host,port\ndbname,user,password,host,port\n'
    with patch('builtins.open', new_callable=mock_open, read_data=read_data):
        mocker.patch('pandas.read_csv', return_value=pd.DataFrame({
            'dbname': ['dbname'],
            'user': ['user'],
            'password': ['password'],
            'host': ['host'],
            'port': ['port']
        }))

        mocker.patch('os.path.join', return_value=db_file_path)

        yield db_file_path


def as_csv_file(data: [[str]]) -> StringIO:
    file_object = StringIO()
    writer = csv.writer(file_object)
    writer.writerows(data)
    file_object.seek(0)

    return file_object


def test_that_environment_variables_set_correctly(mocker):
    # Arrange
    expected_env_vars = {
        "RDS_DB_NAME": "test_db",
        "RDS_HOSTNAME": "test_host",
        "RDS_USERNAME": "test_user",
        "RDS_PASSWORD": "test_password",
        "RDS_PORT": "1234"
    }

    mocker.patch.dict(os.environ, {
        "RDS_DB_NAME": "test_db",
        "RDS_HOSTNAME": "test_host",
        "RDS_USERNAME": "test_user",
        "RDS_PASSWORD": "test_password",
        "RDS_PORT": "1234"
    })

    # Act & Assert
    for key, expected_value in expected_env_vars.items():
        assert os.environ.get(key) == expected_value, f"Env var {key} expected to be {expected_value} but got {os.environ.get(key)}"


def test_that_connection_string_returns_expected_dsn_when_0_params_passed_and_environment_variables_used(mocker, mock_pandas_read_csv):
    # Arrange
    mocker.patch.dict(os.environ, {
        "RDS_DB_NAME": "dbname",
        "RDS_HOSTNAME": "host",
        "RDS_USERNAME": "user",
        "RDS_PASSWORD": "password",
        "RDS_PORT": "port"
    })

    expected_dsn = f"dbname={'dbname'} user={'user'} password={'password'} host={'host'} port={'port'}"

    # Act
    dsn = connection_string()

    # Assert
    assert dsn == expected_dsn, f"expected dsn to be {expected_dsn} but got {dsn}"


def test_that_connection_string_returns_expected_dsn_when_0_params_passed_and_file_path_used(mocker, mock_pandas_read_csv):
    # Arrange
    expected_dsn = f"dbname={'dbname'} user={'user'} password={'password'} host={'host'} port={'port'}"

    mocker.patch.dict(os.environ, {
        "RDS_DB_NAME": "",
        "RDS_HOSTNAME": "",
        "RDS_USERNAME": "",
        "RDS_PASSWORD": "",
        "RDS_PORT": ""
    })

    # Act
    dsn = connection_string()

    # Assert
    assert dsn == expected_dsn, f"expected dsn to be {expected_dsn} but got {dsn}"


def test_that_connection_string_returns_expected_dsn_when_csv_passed(mocker):
    # Arrange
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "host", "port"]]

    expected_dsn =  f"dbname={'mydb'} user={'myuser'} password={'mypassword'} host={'host'} port={'port'}"

    mocker.patch.dict(os.environ, {
        "RDS_DB_NAME": "",
        "RDS_HOSTNAME": "",
        "RDS_USERNAME": "",
        "RDS_PASSWORD": "",
        "RDS_PORT": ""
    })

    # Act
    dsn = connection_string(as_csv_file(database_info))

    # Assert
    assert dsn == expected_dsn, f"expected dsn to be {expected_dsn} but got {dsn}"


@patch('sys.stderr.write')
@patch('sys.exit')
def test_that_connection_string_exits_when_invalid_file_passed(mock_exit, mock_stderr_write):
    # Arrange
    invalid_file = "invalid_file"
    expected_error_message = f"Must either use default csv file path or pass in a csv file, got {type(invalid_file)}."

    # Act and Assert
    with pytest.raises(SystemExit) as e:
        _ = connection_string(invalid_file)

    assert str(e.value) == expected_error_message, f"expected system to exit with {expected_error_message} but got {str(e.value)}"
