# Stage 1: Build the React Application
FROM node:18-alpine AS builder

WORKDIR /app

# Accept backend API URL as a build argument (CRA embeds env vars at build time)
ARG REACT_APP_API_URL=http://localhost:5050/api
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Install dependencies (copying package files first for Docker layer caching)
COPY package.json package-lock.json ./
RUN npm ci --silent

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:stable-alpine

# Remove default nginx config and add our SPA-aware config
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
