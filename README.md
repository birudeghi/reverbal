# Reverbal Server

Reverbal generates insights for your verbal conversation as it happens, helping you close that important sales call or discussing travel plans with your friend.

This server utilises Whisper and ChatGPT APIs to transcribe your audio and generate insights respsctively. You can adjust how ChatGPT generates insights by sending a prompt prior to starting the audio stream from your client.

# Run

Pull docker image:
```
docker pull birudeghi/continuousgpt:beta
```
Use your own OpenAI token in `docker-compose.yaml`:
```
OPENAI_KEY=<your-own-key-here>
```
Run docker:
```
docker-compose up -d
```

# API Reference

This server works on a simple WebSocket connection that accepts different types of events.

## To Server

WebSockets `ws://localhost:80/`

### **********`prompt`********** event
Sets a prompt to be sent together with your transcribed text.

```json
{ 
 "event": "prompt",
 "prompt": "This is a message to customers in a call centre: "
}
```

### **`media`** event
Audio streams in chunks that will be aggregated before being transcribed upon **`stop`** or **`break`** event.

```json
{ 
 "event": "media",
 "sequenceNumber": "3", 
 "media": "no+JhoaJjpzSHxAKBgYJDhtEopGKh4aIjZm7JhILBwYIDRg1qZSLh4aIjJevLBUMBwYHDBUsr5eMiIaHi5SpNRgNCAYHCxImu5mNiIaHipGiRBsOCQYGChAf0pyOiYaGiY+e/x4PCQYGCQ4cUp+QioaGiY6bxCIRCgcGCA0ZO6aSi4eGiI2YtSkUCwcGCAwXL6yVjIeGh4yVrC8XDAgGBwsUKbWYjYiGh4uSpjsZDQgGBwoRIsSbjomGhoqQn1IcDgkGBgkPHv+ej4mGhomOnNIfEAoGBgkOG0SikYqHhoiNmbsmEgsHBggNGDWplIuHhoiMl68sFQwHBgcMFSyvl4yIhoeLlKk1GA0IBgcLEia7mY2IhoeKkaJEGw4JBgYKEB/SnI6JhoaJj57/Hg8JBgYJDhxSn5CKhoaJjpvEIhEKBwYIDRk7ppKLh4aIjZi1KRQLBwYIDBcvrJWMh4aHjJWsLxcMCAYHCxQptZiNiIaHi5KmOxkNCAYHChEixJuOiYaGipCfUhwOCQYGCQ8e/56PiYaGiY6c0h8QCgYGCQ4bRKKRioeGiI2ZuyYSCwcGCA0YNamUi4eGiIyXrywVDAcGBwwVLK+XjIiGh4uUqTUYDQgGBwsSJruZjYiGh4qRokQbDgkGBgoQH9KcjomGhomPnv8eDwkGBgkOHFKfkIqGhomOm8QiEQoHBggNGTumkouHhoiNmLUpFAsHBggMFy+slYyHhoeMlawvFwwIBgcLFCm1mI2IhoeLkqY7GQ0IBgcKESLEm46JhoaKkJ9SHA4JBgYJDx7/no+JhoaJjpzSHxAKBgYJDhtEopGKh4aIjZm7JhILBwYIDRg1qZSLh4aIjJevLBUMBwYHDBUsr5eMiIaHi5SpNRgNCAYHCxImu5mNiIaHipGiRBsOCQYGChAf0pyOiYaGiY+e/x4PCQYGCQ4cUp+QioaGiY6bxCIRCgcGCA0ZO6aSi4eGiI2YtSkUCwcGCAwXL6yVjIeGh4yVrC8XDAgGBwsUKbWYjYiGh4uSpjsZDQgGBwoRIsSbjomGhoqQn1IcDgkGBgkPHv+ej4mGhomOnNIfEAoGBgkOG0SikYqHhoiNmbsmEgsHBggNGDWplIuHhoiMl68sFQwHBgcMFSyvl4yIhoeLlKk1GA0IBgcLEia7mY2IhoeKkaJEGw4JBgYKEB/SnI6JhoaJj57/Hg8JBgYJDhxSn5CKhoaJjpvEIhEKBwYIDRk7ppKLh4aIjZi1KRQLBwYIDBcvrJWMh4aHjJWsLxcMCAYHCxQptZiNiIaHi5KmOxkNCAYHChEixJuOiYaGipCfUhwOCQYGCQ8e/56PiYaGiY6c0h8QCgYGCQ4bRKKRioeGiA==" 
}
```

### **`break`** event
Aggregates collected audio streams to be transcribed. Does not close the connection.

```json
{
  "event": "break"
}
```

### **`stop`** event
Aggregates collected audio streams to be transcribed and then closes the connection.
```json
{
  "event": "stop"
}
```

## From Server

WebSockets `ws://localhost:80/`
### Stream response
```json
{
  "text": "",
  "stream": "start"
}
------
{
  "text": "This is the nature of...",
  "stream": "streaming"
}
------
{
  "text": "",
  "stream": "stop"
}
```
### Error response
```json
{
  "error": "There's a problem..."
}
```

# Debug

To debug, create an .env file in root for your OpenAI token and run:
```
python app.py
```
