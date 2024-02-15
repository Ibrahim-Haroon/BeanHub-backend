"""
This file is used to connect to the AWS RDS database.
"""
# pylint: disable=R0801
from os import path
from os import getenv as env
from io import StringIO
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def connection_string(
        csv_file: StringIO = None
) -> str:
    """

    @rtype: str
    @param csv_file: used for unit tests and if you want to pass in own database authentication
    @return: connection string for AWS RDS
    """
    db_info_file_path = path.join(path.dirname(path.realpath(__file__)),
                                  "../../other/" + "db_info.csv")
    try:
        df = pd.read_csv(db_info_file_path)
    except FileNotFoundError:
        df = pd.DataFrame()

    # pylint: disable=R0916
    if (csv_file is None and
        env('RDS_DB_NAME') and
        env('RDS_USERNAME') and
        env('RDS_PASSWORD') and
        env('RDS_HOSTNAME') and
        env('RDS_PORT')
    ):
        dsn = (f"dbname={env('RDS_DB_NAME')} "
               f"user={env('RDS_USERNAME')} "
               f"password={env('RDS_PASSWORD')} "
               f"host={env('RDS_HOSTNAME')} "
               f"port={env('RDS_PORT')}")
    else:
        if csv_file is None and not df.empty:
            pass
        elif isinstance(csv_file, StringIO):
            df = pd.read_csv(csv_file)
        else:
            raise SystemExit(f"Must either use default csv file path or pass in a csv file,"
                             f" got {type(csv_file)}.")

        row = df.iloc[0]

        dsn = (f"dbname={row['dbname']} "
               f"user={row['user']} "
               f"password={row['password']} "
               f"host={row['host']} "
               f"port={row['port']}")

    return dsn


if __name__ == "__main__":  # pragma: no cover
    print(connection_string())
