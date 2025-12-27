"""Create a demo conversation for testing the comments feature."""

import httpx
import asyncio

async def create_demo():
    async with httpx.AsyncClient() as client:
        # Create conversation
        conv = await client.post('http://localhost:8000/api/conversations',
                                json={'title': 'Comments Feature Demo'})
        conv_id = conv.json()['id']

        # Add messages
        await client.post(
            f'http://localhost:8000/api/conversations/{conv_id}/messages',
            json={'role': 'user', 'content': 'Can you explain React hooks?'}
        )

        await client.post(
            f'http://localhost:8000/api/conversations/{conv_id}/messages',
            json={'role': 'assistant', 'content': '''React hooks are functions that let you use state and other React features in functional components. Here are the most common hooks:

**useState**: Manages state within a component
**useEffect**: Handles side effects like API calls
**useContext**: Accesses context values
**useReducer**: Manages complex state logic
**useCallback**: Memoizes functions
**useMemo**: Memoizes expensive calculations

Hooks make functional components as powerful as class components!'''}
        )

        await client.post(
            f'http://localhost:8000/api/conversations/{conv_id}/messages',
            json={'role': 'user', 'content': 'Can you give me an example of useState?'}
        )

        await client.post(
            f'http://localhost:8000/api/conversations/{conv_id}/messages',
            json={'role': 'assistant', 'content': '''Sure! Here's a simple example:

```javascript
import { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
}
```

The `useState` hook returns an array with the current state value and a function to update it.'''}
        )

        # Share with comments enabled
        share = await client.post(
            f'http://localhost:8000/api/conversations/{conv_id}/share',
            json={'access_level': 'view', 'allow_comments': True, 'expires_in_days': 7}
        )
        share_token = share.json()['share_token']

        # Add a demo comment
        messages_resp = await client.get(f'http://localhost:8000/api/conversations/{conv_id}/messages')
        messages = messages_resp.json()

        await client.post(
            f'http://localhost:8000/api/comments/shared/{share_token}/comments',
            json={
                'message_id': messages[0]['id'],
                'content': 'Great explanation! Can you also explain useEffect?',
                'anonymous_name': 'Curious Learner'
            }
        )

        print('✅ Demo conversation created!')
        print(f'\n📱 Frontend URL: http://localhost:5173/share/{share_token}')
        print(f'🔧 Backend API: http://localhost:8000/api/conversations/share/{share_token}')
        print(f'\nFeatures to test:')
        print('  ✓ View shared conversation')
        print('  ✓ See existing comment on first message')
        print('  ✓ Add new comments to any message')
        print('  ✓ Reply to comments')
        print('  ✓ Edit your own comments')
        print('  ✓ Delete comments')

if __name__ == '__main__':
    asyncio.run(create_demo())
