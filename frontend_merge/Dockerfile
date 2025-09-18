# Step 1: build
FROM node:18-alpine AS builder
WORKDIR /app

# Copy package.json, lock file và tsconfig.json trước
COPY package.json pnpm-lock.yaml* tsconfig.json ./

# Cài dependencies
RUN npm install

# Copy toàn bộ source code
COPY . .

# Build Next.js
RUN npm run build

# Step 2: production image
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# Copy build output + package.json
COPY --from=builder /app/next.config.mjs ./
COPY --from=builder /app/package.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3001

CMD ["npm", "start"]
