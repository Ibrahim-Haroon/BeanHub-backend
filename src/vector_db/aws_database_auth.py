import pandas as pd
from os import path
from io import StringIO
import sys


def connection_string(csv_file: StringIO = None) -> str:
    """

    @rtype: str
    @param csv_file: used for unit tests and if you want to pass in own database authentication
    @return: connection string for AWS RDS
    """
    if csv_file is None:
        db_info_file_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other", "database-info.csv")
        df = pd.read_csv(db_info_file_path)
    elif isinstance(csv_file, StringIO):
        df = pd.read_csv(csv_file)
    else:
        raise SystemExit(f"Must either use default csv file path or pass in a csv file, got {type(csv_file)}.")

    row = df.iloc[0]

    dsn = f"dbname={row['dbname']} user={row['user']} password={row['password']} host={row['host']} port={row['port']}"

    return dsn


if __name__ == "__main__":
    connection_string()