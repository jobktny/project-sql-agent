"use client";

import { Thread } from "@/components/thread";
import { StreamProvider } from "@/providers/Stream";
import { ThreadProvider } from "@/providers/Thread";
import { PyodideProvider } from "@/providers/Pyodide";
import { ArtifactProvider } from "@/components/thread/artifact";
import { Toaster } from "@/components/ui/sonner";
import React from "react";

export default function DemoPage(): React.ReactNode {
  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <Toaster />
      <ThreadProvider>
        <StreamProvider>
          <PyodideProvider>
            <ArtifactProvider>
              <Thread />
            </ArtifactProvider>
          </PyodideProvider>
        </StreamProvider>
      </ThreadProvider>
    </React.Suspense>
  );
}