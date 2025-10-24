# Use official Node.js base image
FROM node:14-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including react-scripts & express)
RUN npm install

# Copy rest of the application
COPY . .

# Build the React app (creates /app/build)
RUN npm run build

# Install express (if not already included in package.json)
RUN npm install express

# Copy HTTPS server entry point
COPY server.js .

# Expose HTTPS port
EXPOSE 3000

# Start HTTPS server
CMD ["node", "server.js"]
