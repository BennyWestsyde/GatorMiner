#!/bin/bash
printf "\n[+] (Mac) Running Docker Container"
docker container run --name devi -d -p 8501:8501 benwest66/gatorminer && echo "Please open \x1B]8;;URI\x1B\\localhost:80\x1B]8;;\x1B\\ on your browser of choice"
