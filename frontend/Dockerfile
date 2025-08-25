# ===== Build =====
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* /app/
RUN npm install
COPY . /app
RUN npm run build

# ===== Serve =====
FROM nginx:alpine
# Use our nginx config that proxies /api -> api:8080
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Serve the built static files
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
