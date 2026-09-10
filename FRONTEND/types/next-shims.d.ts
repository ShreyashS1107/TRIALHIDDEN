declare module 'next' {
  export type Metadata = {
    title?: string | { default: string; template: string };
    description?: string;
    [key: string]: any;
  };
  export type Viewport = any;
  export type NextPage<P = {}, IP = P> = (props: P) => React.ReactNode;
  const next: (options?: any) => any;
  export default next;
}

declare module 'next/link' {
  import React from 'react';
  const Link: React.ComponentType<any>;
  export default Link;
}

declare module 'next/image' {
  import React from 'react';
  const Image: React.ComponentType<any>;
  export default Image;
}

declare module 'next/dist/lib/metadata/types/metadata-interface.js' {
  export type ResolvingMetadata = any;
  export type ResolvingViewport = any;
}

declare module 'next/navigation' {
  export function useRouter(): any;
  export function usePathname(): string;
  export function useSearchParams(): any;
  export function useParams(): any;
  export function notFound(): never;
  export function redirect(url: string, type?: any): never;
}

declare module 'next/server' {
  export class NextRequest extends Request {
    nextUrl: URL;
    cookies: any;
    ip?: string;
    geo?: any;
  }
  export class NextResponse extends Response {
    static json(data: any, init?: ResponseInit): NextResponse;
    static redirect(url: string | URL, init?: number | ResponseInit): NextResponse;
    static rewrite(destination: string | URL, init?: ResponseInit): NextResponse;
    static next(init?: ResponseInit): NextResponse;
  }
}

declare module 'next/server.js' {
  export class NextRequest extends Request {
    nextUrl: URL;
    cookies: any;
    ip?: string;
    geo?: any;
  }
  export class NextResponse extends Response {
    static json(data: any, init?: ResponseInit): NextResponse;
    static redirect(url: string | URL, init?: number | ResponseInit): NextResponse;
    static rewrite(destination: string | URL, init?: ResponseInit): NextResponse;
    static next(init?: ResponseInit): NextResponse;
  }
}

declare module 'next/navigation.js' {
  export function useRouter(): any;
  export function usePathname(): string;
  export function useSearchParams(): any;
  export function useParams(): any;
  export function notFound(): never;
  export function redirect(url: string, type?: any): never;
}
