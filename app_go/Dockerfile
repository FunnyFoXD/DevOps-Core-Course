FROM golang:1.23-alpine AS builder

WORKDIR /src

COPY go.mod ./
RUN go mod download

COPY main.go ./
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o /out/devops-info-service main.go

FROM scratch
COPY --from=builder /out/devops-info-service /devops-info-service

EXPOSE 5000
ENTRYPOINT [ "/devops-info-service" ]