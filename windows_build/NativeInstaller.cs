using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

[assembly: AssemblyTitle("KerbSignal")]
[assembly: AssemblyProduct("KerbSignal")]
[assembly: AssemblyVersion("__APP_VERSION__.0")]
[assembly: AssemblyFileVersion("__APP_VERSION__.0")]

internal static class NativeInstaller {
    // Build tool replaces this token with the exact embedded archive digest.
    private const string PayloadHash = "__PAYLOAD_SHA256__";
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool MoveFileEx(string source, string destination, int flags);

    private static string Hex(byte[] data) { return BitConverter.ToString(data).Replace("-", "").ToLowerInvariant(); }
    private static Stream Resource(string name) {
        Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(name);
        if (stream == null) throw new IOException("The application package is incomplete.");
        return stream;
    }
    private static void AtomicWrite(string target, byte[] bytes) {
        string temporary = target + ".next-" + Guid.NewGuid().ToString("N");
        File.WriteAllBytes(temporary, bytes);
        if (!MoveFileEx(temporary, target, 9)) throw new IOException("Could not finish updating the application. Close KerbSignal and retry.");
    }
    private static void Shortcut(string path, string launcher, string folder) {
        Type shellType = Type.GetTypeFromProgID("WScript.Shell");
        object shell = Activator.CreateInstance(shellType);
        object link = null;
        try {
            link = shellType.InvokeMember("CreateShortcut", BindingFlags.InvokeMethod, null, shell, new object[] { path });
            Type type = link.GetType();
            type.InvokeMember("TargetPath", BindingFlags.SetProperty, null, link, new object[] { launcher });
            type.InvokeMember("WorkingDirectory", BindingFlags.SetProperty, null, link, new object[] { folder });
            type.InvokeMember("Description", BindingFlags.SetProperty, null, link, new object[] { "KerbSignal local race engineer" });
            type.InvokeMember("Save", BindingFlags.InvokeMethod, null, link, null);
        } finally {
            if (link != null) Marshal.ReleaseComObject(link);
            Marshal.ReleaseComObject(shell);
        }
    }
    private static void Install(string destination, bool verify, Action<int, string> progress) {
        if (!Environment.Is64BitOperatingSystem) throw new IOException("KerbSignal requires 64-bit Windows.");
        if (!verify) {
            try {
                using (Mutex existing = Mutex.OpenExisting(@"Local\RaceEngineerApp")) {
                    throw new IOException("Close KerbSignal before updating, then run this installer again. Your saved laps and settings will be kept.");
                }
            } catch (WaitHandleCannotBeOpenedException) { }
        }
        destination = Path.GetFullPath(destination);
        string versions = Path.Combine(destination, "versions");
        Directory.CreateDirectory(versions);
        // Each repair gets a fresh runtime, including when the package is the
        // same version. Never reuse a folder that may have missing files.
        string version = "__APP_VERSION__-" + PayloadHash.Substring(0, 12) + "-" + Guid.NewGuid().ToString("N").Substring(0, 8);
        string runtime = Path.Combine(versions, version);
        if (!Directory.Exists(runtime)) {
            string staging = Path.Combine(versions, ".installing-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(staging);
            string prefix = Path.GetFullPath(staging) + Path.DirectorySeparatorChar;
            progress(1, "Checking the application package…");
            using (Stream payload = Resource("KerbSignal.Payload.zip")) {
                using (SHA256 sha = SHA256.Create())
                    if (Hex(sha.ComputeHash(payload)) != PayloadHash) throw new IOException("The application package failed its integrity check. Download it again.");
                payload.Position = 0;
                using (ZipArchive archive = new ZipArchive(payload, ZipArchiveMode.Read)) {
                    int count = 0;
                    foreach (ZipArchiveEntry entry in archive.Entries) {
                        string target = Path.GetFullPath(Path.Combine(staging, entry.FullName.Replace('/', Path.DirectorySeparatorChar)));
                        if (!target.StartsWith(prefix, StringComparison.OrdinalIgnoreCase) || entry.FullName.Contains(":"))
                            throw new IOException("An invalid package path was rejected.");
                        if (entry.FullName.EndsWith("/")) Directory.CreateDirectory(target);
                        else {
                            Directory.CreateDirectory(Path.GetDirectoryName(target));
                            using (Stream input = entry.Open())
                            using (FileStream output = new FileStream(target, FileMode.CreateNew, FileAccess.Write, FileShare.None)) input.CopyTo(output);
                        }
                        count++;
                        if (count % 20 == 0) progress(5 + count * 85 / archive.Entries.Count, "Installing the local race engineer…");
                    }
                }
            }
            if (!File.Exists(Path.Combine(staging, "pythonw.exe")) || !File.Exists(Path.Combine(staging, "launch.pyw")))
                throw new IOException("The application runtime is incomplete.");
            // Earlier versions stay intact. Publish this runtime only after extraction.
            Directory.Move(staging, runtime);
        }
        byte[] launcher;
        using (Stream input = Resource("KerbSignal.Launcher.exe"))
        using (MemoryStream buffer = new MemoryStream()) { input.CopyTo(buffer); launcher = buffer.ToArray(); }
        string launchPath = Path.Combine(destination, "KerbSignal.exe");
        AtomicWrite(launchPath, launcher);
        AtomicWrite(Path.Combine(destination, "current.ini"), Encoding.UTF8.GetBytes("[App]\r\nVersion=" + version + "\r\n"));
        progress(95, "Finishing…");
        if (!verify) {
            string programs = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "KerbSignal");
            Directory.CreateDirectory(programs);
            Shortcut(Path.Combine(programs, "KerbSignal.lnk"), launchPath, destination);
            Shortcut(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "KerbSignal.lnk"), launchPath, destination);
        }
        progress(100, "KerbSignal is ready.");
        if (!verify) Process.Start(new ProcessStartInfo(launchPath) { WorkingDirectory = destination, UseShellExecute = false, CreateNoWindow = true });
    }
    [STAThread] private static int Main(string[] args) {
        bool verify = Array.Exists(args, arg => arg.Equals("/VERIFY", StringComparison.OrdinalIgnoreCase));
        string destination = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "RaceEngineer");
        bool supplied = false;
        foreach (string arg in args) if (arg.StartsWith("/D=", StringComparison.OrdinalIgnoreCase)) { destination = arg.Substring(3); supplied = true; }
        if (verify) {
            if (!supplied || !Path.IsPathRooted(destination)) return 2;
            try { Install(destination, true, (number, label) => { }); return 0; }
            catch (Exception error) {
                Directory.CreateDirectory(destination);
                File.WriteAllText(Path.Combine(destination, "verification_error.txt"), error.ToString());
                return 1;
            }
        }
        Application.EnableVisualStyles();
        using (Form form = new Form()) {
            form.Text = "KerbSignal"; form.ClientSize = new Size(500, 210);
            form.FormBorderStyle = FormBorderStyle.FixedDialog; form.MaximizeBox = false; form.MinimizeBox = false;
            form.StartPosition = FormStartPosition.CenterScreen; form.BackColor = Color.FromArgb(12, 17, 20);
            Label title = new Label { Text = "KERBSIGNAL", Location = new Point(28, 25), AutoSize = true, ForeColor = Color.FromArgb(184, 241, 124), Font = new Font("Segoe UI", 22, FontStyle.Bold) };
            Label status = new Label { Text = "Preparing your local race engineer…", Location = new Point(30, 84), Size = new Size(440, 45), ForeColor = Color.FromArgb(238, 245, 241), Font = new Font("Segoe UI", 11) };
            ProgressBar bar = new ProgressBar { Location = new Point(30, 146), Size = new Size(440, 16), Minimum = 0, Maximum = 100 };
            form.Controls.Add(title); form.Controls.Add(status); form.Controls.Add(bar);
            int exitCode = 0; bool done = false;
            form.FormClosing += (sender, e) => { if (!done) e.Cancel = true; };
            form.Shown += (sender, e) => Task.Run(() => {
                try {
                    Install(destination, false, (number, label) => form.BeginInvoke(new Action(() => { bar.Value = number; status.Text = label; })));
                } catch (Exception error) {
                    exitCode = 1;
                    form.Invoke(new Action(() => MessageBox.Show(form, error.Message, "KerbSignal", MessageBoxButtons.OK, MessageBoxIcon.Error)));
                } finally { form.BeginInvoke(new Action(() => { done = true; form.Close(); })); }
            });
            Application.Run(form);return exitCode;
        }
    }
}
