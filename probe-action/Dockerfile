FROM ghcr.io/puppeteer/puppeteer:17.0.0
# Set the working directory
WORKDIR /home/pptruser/src
# Copy your application files
COPY . .
# Install Puppeteer
RUN npm install puppeteer
ENTRYPOINT [ "/bin/bash", "-c", "node -e \"$(</home/pptruser/src/probe.js)\"" ]