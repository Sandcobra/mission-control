from setuptools import setup, find_packages

setup(
    name="mission-control-client",
    version="1.0.0",
    description="Python SDK for agents to register and report into Mission Control.",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Mission Control",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.28.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.24.0",
            "respx>=0.21.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "mc-openclaw=mission_control_client.openclaw_wrapper:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
