# Build the React frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app

COPY apps/frontend/package.json apps/frontend/
RUN npm install --prefix apps/frontend

COPY apps/frontend apps/frontend
RUN npm run build --prefix apps/frontend

# Build the frontend gateway service
FROM node:18-alpine AS gateway
WORKDIR /app

COPY services/frontend-gateway/package.json services/frontend-gateway/
RUN npm install --prefix services/frontend-gateway

COPY services/frontend-gateway services/frontend-gateway
COPY --from=frontend-build /app/apps/frontend/build apps/frontend/build

WORKDIR /app/services/frontend-gateway
EXPOSE 3000
CMD ["npm", "start"]
