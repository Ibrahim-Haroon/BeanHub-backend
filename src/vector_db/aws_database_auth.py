import pandas as pd
from os import path
from io import StringIO
from os import getenv as env
from dotenv import load_dotenv

load_dotenv()


def connection_string(csv_file: StringIO = None) -> str:
    """

    @rtype: str
    @param csv_file: used for unit tests and if you want to pass in own database authentication
    @return: connection string for AWS RDS
    """
    db_info_file_path = path.join(path.dirname(path.realpath(__file__)), "../../other/" + "db_info.csv")
    try:
        df = pd.read_csv(db_info_file_path)
    except FileNotFoundError:
        df = None
        pass

    if csv_file is None and env('RDS_DB_NAME') and env('RDS_USERNAME') and env('RDS_PASSWORD') and env('RDS_HOSTNAME') and env('RDS_PORT'):
        dsn = f"dbname={env('RDS_DB_NAME')} user={env('RDS_USERNAME')} password={env('RDS_PASSWORD')} host={env('RDS_HOSTNAME')} port={env('RDS_PORT')}"
    else:
        if csv_file is None and not df.empty:
            pass
        elif isinstance(csv_file, StringIO):
            df = pd.read_csv(csv_file)
        else:
            raise SystemExit(f"Must either use default csv file path or pass in a csv file, got {type(csv_file)}.")

        row = df.iloc[0]

        dsn = f"dbname={row['dbname']} user={row['user']} password={row['password']} host={row['host']} port={row['port']}"

    return dsn


if __name__ == "__main__":
    print(connection_string())
