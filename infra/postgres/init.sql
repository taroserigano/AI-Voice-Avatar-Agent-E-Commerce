-- A separate database for integration tests, so running tests never touches dev data.
CREATE DATABASE commerce_test OWNER commerce;
