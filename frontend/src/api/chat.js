/**
 * Chat API Module
 * ================
 * Handles streaming communication with the LangChain chatbot endpoint.
 *
 * WHY NOT AXIOS FOR STREAMING?
 * -----------------------------
 * Axios buffers the entire response before resolving the promise.
 * For streaming (token by token), we need the native Fetch API,
 * which gives us access to the raw ReadableStream.
 *
 * HOW STREAMING WORKS (step by step):
 * -------------------------------------
 * 1. fetch() opens a persistent HTTP connection to /api/v1/chat
 * 2. FastAPI sends text chunks as the LLM generates them
 * 3. We get a ReadableStream from response.body
 * 4. A reader reads chunks in a loop
 * 5. Each chunk is decoded (bytes → string) and passed to onChunk()
 * 6. Your component calls setMessage(prev => prev + chunk) to update the UI
 * 7. When the LLM finishes, the stream closes and we call onDone()
 *
 * This is why chat feels "live" — you see words appear as they're generated.
 *
 * LEARN MORE:
 *   ReadableStream:    https://developer.mozilla.org/en-US/docs/Web/API/ReadableStream
 *   Fetch streaming:   https://developer.mozilla.org/en-US/docs/Web/API/Streams_API/Using_readable_streams
 */

const API_BASE = import.meta.env.VITE_API_URL || ''

/**
 * Send a message to the chatbot and stream the response.
 *
 * @param {object} params
 * @param {string}        params.message             - The user's message text
 * @param {object|null}   params.playerContext        - Current player data (from fetchPlayerAnalytics)
 *                                                     Gives the LLM context about who you're discussing
 * @param {Array}         params.conversationHistory  - Previous messages [{role, content}, ...]
 * @param {Function}      params.onChunk              - Called with each text chunk as it arrives
 *                                                     e.g., (chunk) => setResponse(prev => prev + chunk)
 * @param {Function}      params.onDone               - Called when streaming is complete
 * @param {Function}      params.onError              - Called if the request fails
 *
 * TODO: Implement this function.
 *
 * STEP 1 — Start with a non-streaming version:
 *   const res = await fetch(`${API_BASE}/api/v1/chat`, {
 *     method: 'POST',
 *     headers: { 'Content-Type': 'application/json' },
 *     body: JSON.stringify({ message, player_context: playerContext, conversation_history: conversationHistory })
 *   })
 *   const data = await res.json()
 *   onChunk(data.response)
 *   onDone()
 *
 * STEP 2 — Add streaming once step 1 works:
 *   const reader = response.body.getReader()
 *   const decoder = new TextDecoder()
 *   while (true) {
 *     const { done, value } = await reader.read()
 *     if (done) { onDone(); break }
 *     onChunk(decoder.decode(value, { stream: true }))
 *   }
 */
export async function streamChat({
  message,
  playerContext = null,
  conversationHistory = [],
  onChunk,
  onDone,
  onError,
}) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        player_context: playerContext,
        conversation_history: conversationHistory,
      }),
    })

    if (!res.ok) throw new Error(`Chat error: ${res.status}`)

    const reader = res.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      onChunk(decoder.decode(value, { stream: true }))
    }

    onDone()
  } catch (err) {
    onError(err)
  }
}
