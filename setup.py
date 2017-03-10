from setuptools import setup

setup(
    name='raven-bash 2',
    version='0.1.0',
    description='Raven Sentry client for Bash.',
    classifiers=[],
    keywords='raven sentry bash',
    license='Apache License 2.0',
    install_requires=[
        'raven>=6.0.0',
    ],
    extras_require = {
        'requests': ['requests']
    },
    packages=['logger'],
    package_data={'logger': ['raven-bash', 'logger/*.py']},
    entry_points={
        'console_scripts': [
            'raven-logger=logger.raven_logger:main',
        ],
    },
    scripts=['raven-bash'],
    zip_safe=False
)
