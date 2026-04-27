# --- Stage 1: Build React/Vite ---
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# --- Stage 2: Serve ---
FROM nginx:alpine

# Generate a self-signed certificate natively
RUN apk add --no-cache openssl \
    && mkdir -p /etc/nginx/ssl \
    && openssl req -x509 -nodes -days 365 \
       -newkey rsa:2048 \
       -keyout /etc/nginx/ssl/selfsigned.key \
       -out /etc/nginx/ssl/selfsigned.crt \
       -subj "/CN=mtg-scanner"

# Copy custom Nginx routing configurations securely
COPY nginx.conf /etc/nginx/nginx.conf

# Map strictly the /dist payload securely into web roots
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
EXPOSE 443

CMD ["nginx", "-g", "daemon off;"]
