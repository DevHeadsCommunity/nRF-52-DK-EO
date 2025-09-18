FROM ubuntu:24.04
# Check if "ubuntu" user exists, delete it if it does, then create the desired user
RUN if getent passwd ubuntu > /dev/null 2>&1; then \
    userdel -r ubuntu && \
    echo "Deleted existing ubuntu user"; \
    fi