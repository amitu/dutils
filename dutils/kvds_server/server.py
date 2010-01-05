import set_paths, path

if __name__ == "__main__":
    from dutils import pld
    APP_DIR=path.path(__file__).parent.abspath()
    pld.handle(
        INSTALLED_APPS=["dutils"], DEBUG=True,
        ROOT_URLCONF="dutils.kvds_server.urls", APP_DIR=APP_DIR
    )

