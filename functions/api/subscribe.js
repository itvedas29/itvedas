export default {
  async fetch(request, env) {
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ success: false, message: 'Method not allowed' }), { status: 405 });
    }

    try {
      const { email, timestamp } = await request.json();

      if (!email || !email.includes('@')) {
        return new Response(JSON.stringify({ success: false, message: 'Invalid email' }), { status: 400 });
      }

      // Validate email format
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        return new Response(JSON.stringify({ success: false, message: 'Invalid email format' }), { status: 400 });
      }

      // Store in KV if available, otherwise in-memory
      const subscribers = await env.SUBSCRIBERS?.get('list') || '[]';
      const list = JSON.parse(subscribers);

      // Check for duplicates
      if (list.some(s => s.email === email)) {
        return new Response(JSON.stringify({ success: false, message: 'Already subscribed' }), { status: 400 });
      }

      // Add new subscriber
      list.push({
        email,
        timestamp: timestamp || new Date().toISOString(),
        verified: false,
        source: 'homepage-signup'
      });

      // Save back
      if (env.SUBSCRIBERS) {
        await env.SUBSCRIBERS.put('list', JSON.stringify(list, null, 2));
      }

      return new Response(JSON.stringify({
        success: true,
        message: 'Successfully subscribed',
        count: list.length
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error) {
      console.error('Subscribe error:', error);
      return new Response(JSON.stringify({
        success: false,
        message: 'Server error: ' + error.message
      }), { status: 500 });
    }
  }
}
