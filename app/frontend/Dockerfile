FROM node:20-alpine

WORKDIR /app

ARG VITE_API_URL
ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

# Install dependencies first for better layer caching.
COPY package.json package-lock.json* ./
RUN npm install

# Build the static Vite bundle. VITE_* variables must be present at build time
# because Vite embeds them into the generated assets.
COPY . .
RUN npm run build

RUN npm install -g serve

EXPOSE 3000

CMD ["sh", "-c", "serve -s dist -l tcp://0.0.0.0:${PORT:-3000}"]
