import { useState, useEffect, useRef } from 'react';
import { getStreamUrl } from '../api';

/**
 * useAgentStream — subscribes to the live SSE agent pipeline stream.
 * 
 * Usage:
 *   const { events, status, start, reset } = useAgentStream(scenarioId);
 * 
 * status: 'idle' | 'connecting' | 'running' | 'done' | 'error'
 */
export function useAgentStream(scenarioId) {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState('idle'); // idle | connecting | running | done | error
  const sourceRef = useRef(null);

  const start = () => {
    if (!scenarioId) return;
    if (sourceRef.current) {
      sourceRef.current.close();
    }
    setEvents([]);
    setStatus('connecting');

    const url = getStreamUrl(scenarioId);
    const es = new EventSource(url);
    sourceRef.current = es;

    es.onopen = () => setStatus('running');

    es.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        setEvents((prev) => [...prev, payload]);
        if (payload.event_type === 'PIPELINE_COMPLETE') {
          setStatus('done');
          es.close();
        }
        if (payload.event_type === 'ORCHESTRATOR_ERROR') {
          setStatus('error');
          es.close();
        }
      } catch {}
    };

    // Also listen to typed events from SSE
    const TYPED_EVENTS = [
      'ORCHESTRATOR_STATUS', 'AGENT_START', 'AGENT_RESULT',
      'PIPELINE_COMPLETE', 'ORCHESTRATOR_ERROR',
    ];
    TYPED_EVENTS.forEach((evtType) => {
      es.addEventListener(evtType, (e) => {
        try {
          const payload = JSON.parse(e.data);
          setEvents((prev) => {
            const already = prev.find(
              (p) => p.event_type === payload.event_type && p.timestamp === payload.timestamp
            );
            return already ? prev : [...prev, payload];
          });
          if (evtType === 'PIPELINE_COMPLETE') {
            setStatus('done');
            es.close();
          }
          if (evtType === 'ORCHESTRATOR_ERROR') {
            setStatus('error');
            es.close();
          }
        } catch {}
      });
    });

    es.onerror = () => {
      setStatus((s) => (s === 'done' ? 'done' : 'error'));
      es.close();
    };
  };

  const reset = () => {
    if (sourceRef.current) sourceRef.current.close();
    setEvents([]);
    setStatus('idle');
  };

  useEffect(() => () => sourceRef.current?.close(), []);

  return { events, status, start, reset };
}
