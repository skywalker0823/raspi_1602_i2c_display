#!/bin/bash

docker build -t weather-display .
docker run -d --name weather-lcd --restart unless-stopped --privileged --device=/dev/i2c-1 weather-display