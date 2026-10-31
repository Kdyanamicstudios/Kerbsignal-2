using System;
using System.Diagnostics;
using System.IO;
using System.Text.RegularExpressions;
using System.Windows.Forms;

[assembly: System.Reflection.AssemblyTitle("KerbSignal")]
[assembly: System.Reflection.AssemblyProduct("KerbSignal")]
[assembly: System.Reflection.AssemblyVersion("0.15.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("0.15.0.0")]

internal static class NativeLauncher {
    [STAThread] private static int Main(string[] args) {
        try {
            string root = AppDomain.CurrentDomain.BaseDirectory;
            string version = null;
            foreach (string line in File.ReadAllLines(Path.Combine(root, "current.ini")))
                if (line.StartsWith("Version=", StringComparison.OrdinalIgnoreCase)) version = line.Substring(8).Trim();
            if (version == null || !Regex.IsMatch(version, @"^[0-9]+\.[0-9]+\.[0-9]+-[a-f0-9]{12}(?:-[a-f0-9]{8})?$"))
                throw new IOException("The installed version could not be located. Run the KerbSignal installer to repair it.");
            string runtime = Path.Combine(root, "versions", version);
            string python = Path.Combine(runtime, "pythonw.exe");
            string script = Path.Combine(runtime, "launch.pyw");
            if (!File.Exists(python) || !File.Exists(script)) throw new IOException("The application runtime is incomplete.");
            if (args.Length == 1 && args[0] == "--check") return 0;
            Process.Start(new ProcessStartInfo(python, "-I \"" + script + "\"") {
                WorkingDirectory = runtime, UseShellExecute = false, CreateNoWindow = true
            });
            return 0;
        } catch (Exception error) {
            if (args.Length == 0) MessageBox.Show(error.Message, "KerbSignal", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
