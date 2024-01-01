import pytest
from mock import mock_open, patch
from src.vector_db.aws_database_auth import connection_string
import pandas as pd
from os import path
from io import StringIO
import csv


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


def test_that_connection_string_returns_expected_dsn_when_0_params_passed(mock_pandas_read_csv):
    # Arrange
    expected_dsn = f"dbname={'dbname'} user={'user'} password={'password'} host={'host'} port={'port'}"

    # Act
    dsn = connection_string()

    # Assert
    assert dsn == expected_dsn, f"expected dsn to be {expected_dsn} but got {dsn}"


def test_that_connection_string_returns_expected_dsn_when_csv_passed():
    # Arrange
    database_info = [
        ["dbname", "user", "password", "host", "port"],
        ["mydb", "myuser", "mypassword", "host", "port"]]

    expected_dsn =  f"dbname={'mydb'} user={'myuser'} password={'mypassword'} host={'host'} port={'port'}"

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


