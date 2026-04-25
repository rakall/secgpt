#!/bin/bash
set -e

echo "=== pentest-agent Container Startup ==="

# Ensure directories exist
mkdir -p "$CONFIG_DIR" "$DATA_DIR" /app/sessions /app/models /app/kb-data
chmod 700 "$CONFIG_DIR" "$DATA_DIR"

# Log configuration
echo "CONFIG_DIR: $CONFIG_DIR"
echo "DATA_DIR: $DATA_DIR"

# Validate LLM provider configuration
ACTIVE_PROVIDER="${ACTIVE_PROVIDER:-local}"
echo "Active LLM provider: $ACTIVE_PROVIDER"

case "$ACTIVE_PROVIDER" in
    openai)
        if [ -z "$OPENAI_API_KEY" ]; then
            echo "ERROR: OPENAI_API_KEY not set but ACTIVE_PROVIDER=openai"
            exit 1
        fi
        echo "✓ OpenAI API key detected"
        ;;
    anthropic)
        if [ -z "$ANTHROPIC_API_KEY" ]; then
            echo "ERROR: ANTHROPIC_API_KEY not set but ACTIVE_PROVIDER=anthropic"
            exit 1
        fi
        echo "✓ Anthropic API key detected"
        ;;
    google)
        if [ -z "$GOOGLE_API_KEY" ]; then
            echo "ERROR: GOOGLE_API_KEY not set but ACTIVE_PROVIDER=google"
            exit 1
        fi
        echo "✓ Google API key detected"
        ;;
    groq)
        if [ -z "$GROQ_API_KEY" ]; then
            echo "ERROR: GROQ_API_KEY not set but ACTIVE_PROVIDER=groq"
            exit 1
        fi
        echo "✓ Groq API key detected"
        ;;
    local)
        echo "Using local embedding model (CPU-based)"
        ;;
    *)
        echo "ERROR: Unknown ACTIVE_PROVIDER: $ACTIVE_PROVIDER"
        exit 1
        ;;
esac

# Create secrets file if using external providers (and not already mounted)
if [ "$ACTIVE_PROVIDER" != "local" ] && [ ! -f "$CONFIG_DIR/secrets" ]; then
    echo "Creating secrets file for external provider..."
    touch "$CONFIG_DIR/secrets"
    chmod 600 "$CONFIG_DIR/secrets"
    
    case "$ACTIVE_PROVIDER" in
        openai)
            echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> "$CONFIG_DIR/secrets"
            ;;
        anthropic)
            echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" >> "$CONFIG_DIR/secrets"
            ;;
        google)
            echo "GOOGLE_API_KEY=$GOOGLE_API_KEY" >> "$CONFIG_DIR/secrets"
            ;;
        groq)
            echo "GROQ_API_KEY=$GROQ_API_KEY" >> "$CONFIG_DIR/secrets"
            ;;
    esac
fi

# Start daemon in background
echo ""
echo "Starting daemon..."
python -m pentest_agent.daemon --embedding-model-path "/app/models" --chroma-dir "$DATA_DIR/chroma" --provider "$ACTIVE_PROVIDER" > "$DATA_DIR/daemon.log" 2>&1 &
DAEMON_PID=$!
echo "Daemon PID: $DAEMON_PID"

# Wait for daemon to be ready (poll /health endpoint)
echo "Waiting for daemon to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:47291/health > /dev/null 2>&1; then
        echo "✓ Daemon is ready"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 1
    if [ $((RETRY_COUNT % 5)) -eq 0 ]; then
        echo "  Still waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "ERROR: Daemon failed to start after ${MAX_RETRIES}s"
    tail -n 20 "$DATA_DIR/daemon.log"
    exit 1
fi

# Handle graceful shutdown
cleanup() {
    echo ""
    echo "=== Shutdown signal received ==="
    echo "Stopping FastAPI server..."
    kill %1 2>/dev/null || true
    
    echo "Stopping daemon..."
    if kill $DAEMON_PID 2>/dev/null; then
        wait $DAEMON_PID 2>/dev/null || true
    fi
    
    echo "✓ Clean shutdown complete"
    exit 0
}

trap cleanup SIGTERM SIGINT

echo ""
echo "Starting FastAPI server on 0.0.0.0:8080..."
python -m pentest_agent.api.main &
wait %1
