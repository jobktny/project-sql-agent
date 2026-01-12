"use client";

import { useState, useEffect, useRef } from "react";
import { Loader2, Code, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePyodideContext } from "@/providers/Pyodide";
import { SyntaxHighlighter } from "./syntax-highlighter";

interface RunnableCodeProps {
    code: string;
    language: string;
    autoRun?: boolean;
}

export function RunnableCode({
    code,
    language,
    autoRun = false,
}: RunnableCodeProps) {
    const { isReady, isLoading: pyodideLoading, runCode } =
        usePyodideContext();

    const [isRunning, setIsRunning] = useState(false);
    const [hasRun, setHasRun] = useState(false);
    const [output, setOutput] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [figure, setFigure] = useState<string | null>(null);
    const [showCode, setShowCode] = useState(!autoRun);

    const figureRef = useRef<HTMLDivElement>(null);
    const hasAutoRunRef = useRef(false);

    useEffect(() => {
        if (!figure || !figureRef.current) return;

        const scripts = figureRef.current.querySelectorAll("script");
        const externalScripts: HTMLScriptElement[] = [];
        const inlineScripts: HTMLScriptElement[] = [];

        scripts.forEach((script) => {
            if (script.src) externalScripts.push(script);
            else inlineScripts.push(script);
        });

        const executeInlineScripts = () => {
            inlineScripts.forEach((oldScript) => {
                const newScript = document.createElement("script");
                newScript.textContent = oldScript.textContent;
                oldScript.parentNode?.replaceChild(newScript, oldScript);
            });
        };

        if ((window as any).Plotly) {
            executeInlineScripts();
            return;
        }

        let loaded = 0;
        externalScripts.forEach((oldScript) => {
            const newScript = document.createElement("script");
            newScript.src = oldScript.src;
            newScript.onload = () => {
                loaded++;
                if (loaded === externalScripts.length) {
                    executeInlineScripts();
                }
            };
            oldScript.parentNode?.replaceChild(newScript, oldScript);
        });

        if (externalScripts.length === 0) {
            executeInlineScripts();
        }
    }, [figure]);

    const executeCode = async () => {
        setIsRunning(true);
        setOutput(null);
        setError(null);
        setFigure(null);

        const result = await runCode(code);

        setOutput(result.output || null);
        setError(result.error || null);
        setFigure(result.figure || null);

        setIsRunning(false);
        setHasRun(true);
        setShowCode(false);
    };

    // Auto-run code when autoRun is true and Pyodide is ready
    useEffect(() => {
        if (autoRun && isReady && !hasAutoRunRef.current && !hasRun) {
            hasAutoRunRef.current = true;
            executeCode();
        }
    }, [autoRun, isReady, hasRun]);

    const renderCodeBlock = () => (
        <div className="rounded-lg overflow-hidden border border-zinc-700">
            <div className="flex items-center justify-between px-3 py-2 bg-zinc-800 border-b border-zinc-700">
                <span className="text-xs text-zinc-400 font-medium uppercase tracking-wide">
                    {language}
                </span>
                <Button
                    size="sm"
                    variant="ghost"
                    onClick={executeCode}
                    disabled={!isReady || isRunning}
                    className="h-7 px-3 text-xs gap-1.5 text-zinc-300 hover:text-white hover:bg-zinc-700"
                >
                    {isRunning ? (
                        <>
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            Running...
                        </>
                    ) : pyodideLoading ? (
                        <>
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            Loading...
                        </>
                    ) : (
                        <>
                            <Play className="h-3.5 w-3.5" />
                            Run
                        </>
                    )}
                </Button>
            </div>
            <SyntaxHighlighter language={language}>
                {code}
            </SyntaxHighlighter>
        </div>
    );

    if (!hasRun) {
        return renderCodeBlock();
    }

    if (error && !figure) {
        return (
            <div className="space-y-2">
                <div className="rounded-lg overflow-hidden border border-red-700">
                    <div className="bg-red-950 p-4">
                        <pre className="text-red-400 text-sm whitespace-pre-wrap">
                            {error}
                        </pre>
                    </div>
                </div>
                {renderCodeBlock()}
            </div>
        );
    }

    return (
        <div className="rounded-lg overflow-hidden space-y-2">
            {figure && (
                <div
                    ref={figureRef}
                    className="bg-white rounded-lg"
                    dangerouslySetInnerHTML={{ __html: figure }}
                />
            )}

            {output && !figure && (
                <pre className="bg-zinc-900 text-green-400 text-sm p-4 whitespace-pre-wrap rounded-lg">
                    {output}
                </pre>
            )}

            <button
                onClick={() => setShowCode(!showCode)}
                className="flex items-center gap-2 px-3 py-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
            >
                <Code className="h-3 w-3" />
                {showCode ? "Hide code" : "View code"}
            </button>

            {showCode && renderCodeBlock()}
        </div>
    );
}