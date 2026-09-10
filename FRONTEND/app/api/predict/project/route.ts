import { NextRequest, NextResponse } from 'next/server';
import { CustomProjectInput } from '@/lib/api/predict';

export async function POST(req: NextRequest) {
  try {
    const body: CustomProjectInput = await req.json();

    if (!body.project_name || !body.project_id || !body.agency || !body.state) {
      return NextResponse.json(
        { 
          error: 'Missing mandatory project identification fields.',
          detail: 'Missing mandatory project identification fields (project_name, project_id, agency, state).' 
        },
        { status: 400 }
      );
    }

    if (!body.original_cost_crore || Number(body.original_cost_crore) <= 0) {
      return NextResponse.json(
        { 
          error: 'Invalid original cost.',
          detail: 'Original / approved cost must be a positive number greater than 0.' 
        },
        { status: 400 }
      );
    }

    if (body.revised_cost_crore !== undefined && Number(body.revised_cost_crore) < Number(body.original_cost_crore)) {
      return NextResponse.json(
        { 
          error: 'Invalid revised cost.',
          detail: 'Revised cost cannot be less than original cost.' 
        },
        { status: 400 }
      );
    }

    if (body.physical_progress_percent !== undefined && (Number(body.physical_progress_percent) < 0 || Number(body.physical_progress_percent) > 100)) {
      return NextResponse.json(
        { 
          error: 'Invalid physical progress.',
          detail: 'Certified physical progress must be between 0 and 100%.' 
        },
        { status: 400 }
      );
    }

    if (body.cumulative_expenditure_crore !== undefined && Number(body.cumulative_expenditure_crore) < 0) {
      return NextResponse.json(
        { 
          error: 'Invalid cumulative expenditure.',
          detail: 'Cumulative expenditure cannot be negative.' 
        },
        { status: 400 }
      );
    }

    const dateRegex = /^\d{4}-(0[1-9]|1[0-2])$/;
    if (!body.approval_start_date || !dateRegex.test(body.approval_start_date)) {
      return NextResponse.json(
        { 
          error: 'Invalid approval date.',
          detail: 'Approval / start date must be a valid month in YYYY-MM format.' 
        },
        { status: 400 }
      );
    }

    if (!body.original_completion_date || !dateRegex.test(body.original_completion_date)) {
      return NextResponse.json(
        { 
          error: 'Invalid completion date.',
          detail: 'Original completion date must be a valid month in YYYY-MM format.' 
        },
        { status: 400 }
      );
    }

    if (body.approval_start_date && body.original_completion_date && body.original_completion_date < body.approval_start_date) {
      return NextResponse.json(
        { 
          error: 'Invalid schedule dates.',
          detail: 'Target completion date must be on or after approval start date.' 
        },
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
          error: 'PAIMANA ML INFERENCE ENGINE UNAVAILABLE',
          detail: 'Start the ML service and try again.'
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

