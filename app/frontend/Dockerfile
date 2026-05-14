# Use a stable Node version
FROM node:20-alpine

WORKDIR /app

# Install dependencies first (better caching)
COPY package.json package-lock.json* ./
RUN npm install

# Copy the rest of the source code
COPY . .

# Use the command recommended in your Railway guide
# This allows Railway to pass the $PORT variable dynamically
CMD ["sh", "-c", "npx vite --host 0.0.0.0 --port $PORT"]