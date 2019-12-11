import pytest


@pytest.fixture(scope="module")
def start_db():
    "Instantiate the test database and create the nodedb tables"
    import chimedb.core as db

    # Turn on test-safe mode
    db.test_enable()

    # Connect to the database.  In test-safe mode, this will create an
    # in-memory SQLite database
    db.connect(read_write=True)

    # Create our tables
    db.orm.create_tables(packages="chimedb.node")


@pytest.fixture(scope="module")
def click_runner():
    "Run a click command"
    from click.testing import CliRunner

    return CliRunner()
