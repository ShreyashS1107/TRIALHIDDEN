import { NextRequest, NextResponse } from 'next/server';
import { CustomProjectInput } from '@/lib/api/predict';

export async function POST(req: NextRequest) {
  try {
    const body: CustomProjectInput = await req.json();

    if (!body.project_name || !body.project_id || !body.agency || !body.state) {
      return NextResponse.json(
        { error: 'Missing mandatory project identification fields (project_name, project_id, agency, state).' },
        { status: 400 }
      );
    }

    if (!body.original_cost_crore || body.original_cost_crore <= 0) {
      return NextResponse.json(
        { error: 'Original / approved cost must be a positive number greater than 0.' },
        { status: 400 }
      );
    }

    // Call FastAPI ML Inference Service (Source of Truth)
    try {
      const fastApiRes = await fetch('http://127.0.0.1:8000/predict/project', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(15000)
      });

      if (fastApiRes.ok) {
        const data = await fastApiRes.json();
        return NextResponse.json(data);
      } else {
        const errJson = await fastApiRes.json().catch(() => ({}));
        return NextResponse.json(
          { error: errJson.detail || `ML inference engine returned status ${fastApiRes.status}` },
          { status: fastApiRes.status }
        );
      }
    } catch (fastApiErr: any) {
      return NextResponse.json(
        {
          error: `PAIMANA ML inference engine is unavailable: ${fastApiErr.message}. The trained ML pipeline is the sole source of truth; client-side approximation is disabled.`
        },
        { status: 503 }
      );
    }
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to process project assessment' },
      { status: 500 }
    );
  }
}

