from setuptools import setup
setup(
    name = "docserver",
    version = "1.0.0",
    packages = [
        'ds',
    ],
    package_dir = {'':'src'},
    entry_points = {
        # 'setuptools.installation': [
        #     'eggsecutable = ds.main:main',
        # ],
        'console_scripts':[
            'docserver = ds.main:main',
        ],
    },
)

