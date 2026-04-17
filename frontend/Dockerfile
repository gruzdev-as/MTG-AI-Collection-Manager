FROM nginx:alpine

# Install openssl to generate a self-signed certificate
RUN apk add --no-cache openssl \
    && mkdir -p /etc/nginx/ssl \
    && openssl req -x509 -nodes -days 365 \
       -newkey rsa:2048 \
       -keyout /etc/nginx/ssl/selfsigned.key \
       -out /etc/nginx/ssl/selfsigned.crt \
       -subj "/CN=mtg-scanner"

COPY nginx.conf /etc/nginx/nginx.conf
COPY . /usr/share/nginx/html
