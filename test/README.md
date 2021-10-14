The tests patch the clients and running of the wrappee software very heavily.
You can run the tests with patching toggled on for quick diagnostic tests, 
then run the tests with the patching toggled off before releasing.
Toggle using `test/config.py::DO_PATCH`