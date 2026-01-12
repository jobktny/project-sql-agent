import { useState, useEffect, useCallback, useRef, useMemo } from "react";
interface PyodideInstance {
    runPythonAsync: (code: string) => Promise<any>;
    loadPackage: (packages: string | string[]) => Promise<void>;
    globals: {
        get: (name: string) => any;
        set: (name: string, value: any) => void;
    };
    pyimport: (name: string) => any;
}

interface UsePyodideResult {
    pyodide: PyodideInstance | null;
    isLoading: boolean;
    isReady: boolean;
    error: Error | null;
    runCode: (code: string) => Promise<{ output: string; error?: string; figure?: string }>;
}


export function usePyodide(): UsePyodideResult {
    const [pyodide, setPyodide] = useState<PyodideInstance | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isReady, setIsReady] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    const initializingRef = useRef(false);

    useEffect(() => {
        if (initializingRef.current || pyodide) return;
        initializingRef.current = true;

        const loadPyodide = async () => {
            setIsLoading(true);
            try {
                // Load Pyodide script
                const script = document.createElement("script");
                script.src = "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js";
                script.async = true;

                await new Promise<void>((resolve, reject) => {
                    script.onload = () => resolve();
                    script.onerror = () => reject(new Error("Failed to load Pyodide"));
                    document.head.appendChild(script);
                });

                // Initialize Pyodide
                const py = await (window as any).loadPyodide({
                    indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/",
                });

                // Pre-load common packages for data viz
                await py.loadPackage(["micropip", "numpy", "pandas"]);

                // Install plotly via micropip
                const micropip = py.pyimport("micropip");
                await micropip.install("plotly");

                setPyodide(py);
                setIsReady(true);
            } catch (err) {
                setError(err as Error);
            } finally {
                setIsLoading(false);
            }
        };

        loadPyodide();
    }, []);

    const runCode = useCallback(
        async (code: string): Promise<{ output: string; error?: string; figure?: string }> => {
            if (!pyodide) {
                return { output: "", error: "Pyodide not loaded" };
            }

            try {
                // Step 1: Setup stdout capture
                await pyodide.runPythonAsync(`
    import sys
    from io import StringIO
    _old_stdout = sys.stdout
    _old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    `);

                // Step 2: Run user code directly (no wrapping)
                let execError = "";
                try {
                    await pyodide.runPythonAsync(code);
                } catch (err: any) {
                    execError = err.message || String(err);
                }

                // Step 3: Capture stdout/stderr
                const stdout = await pyodide.runPythonAsync("sys.stdout.getvalue()");
                const stderr = await pyodide.runPythonAsync("sys.stderr.getvalue()");

                // Step 4: Restore stdout/stderr
                await pyodide.runPythonAsync(`
    sys.stdout = _old_stdout
    sys.stderr = _old_stderr
    `);

                // Step 5: Check for figure using Pyodide's globals API
                let figureHtml = "";
                console.log("funcetion used ", pyodide);
                try {
                    console.log("function used 1");
                    // Use Python to find any Plotly figure in globals and return both name and HTML
                    const result = await pyodide.runPythonAsync(`
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
_fig_html = None
for name, obj in list(globals().items()):
    if not name.startswith('_') and not name in ['go', 'px', 'pio', 'sys', 'StringIO', '_old_stdout', '_old_stderr']:
        try:
            if isinstance(obj, go.Figure):
                _fig_html = pio.to_html(obj, full_html=False, include_plotlyjs="cdn")
                break
        except:
            pass
_fig_html
`);
                    console.log("function used 2", result);
                    if (result && typeof result === 'string' && result.trim()) {
                        figureHtml = result;
                        console.log("Figure HTML generated, length:", figureHtml.length);
                    } else {
                        console.log("No Plotly figure variable found");
                    }
                } catch (err) {
                    console.log("Error detecting figure:", err);
                }

                return {
                    output: stdout || "",
                    error: execError || stderr || undefined,
                    figure: figureHtml || undefined,
                };
            } catch (err: any) {
                console.error("Pyodide error:", err);
                return {
                    output: "",
                    error: err.message || String(err),
                };
            }
        },
        [pyodide]
    );

    return useMemo(
        () => ({ pyodide, isLoading, isReady, error, runCode }),
        [pyodide, isLoading, isReady, error, runCode]
    );
}