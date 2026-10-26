using System;
using System.Diagnostics;

public class UtilTool
{
    /// <summary>
    /// 运行外部exe
    /// </summary>
    /// <param name="exePath">exe路径</param>
    /// <param name="cmdArg">命令行内容</param>
    /// <param name="wait">是否等待执行结果</param>
    /// <returns></returns>
    public static bool CmdExe(string exePath, string cmdArg, bool wait = true)
    {
        bool runSuc = true;

        ProcessStartInfo start = new ProcessStartInfo(exePath);
        start.Arguments = cmdArg;
        start.CreateNoWindow = false;
        start.ErrorDialog = true;
        start.UseShellExecute = false;

        if (start.UseShellExecute)
        {
            start.RedirectStandardOutput = false;
            start.RedirectStandardError = false;
            start.RedirectStandardInput = false;
        }
        else
        {
            start.RedirectStandardOutput = true;
            start.RedirectStandardError = true;
            start.RedirectStandardInput = true;
            start.StandardOutputEncoding = System.Text.UTF8Encoding.UTF8;
            start.StandardErrorEncoding = System.Text.UTF8Encoding.UTF8;
        }

        Process p = Process.Start(start);
        if (!start.UseShellExecute)
        {
            Console.WriteLine(p.StandardOutput.ReadToEnd());
            Console.WriteLine(p.StandardError.ReadToEnd());
        }

        if (wait)
        {
            p.WaitForExit();
            int code = p.ExitCode;
            p.Close();

            Console.WriteLine(exePath + " exe return code: " + code);
            return code == 0;
        }
        return runSuc;
    }

    public static bool CmdExe2(string cmdExe, string workingDir, string args, bool wait = true)
    {
        bool runSuc = true;
        Process p = new Process();
        p.StartInfo.FileName = cmdExe;
        p.StartInfo.Arguments = args;
        p.StartInfo.UseShellExecute = false;
        p.StartInfo.CreateNoWindow = true;
        if (!string.IsNullOrEmpty(workingDir))
            p.StartInfo.WorkingDirectory = workingDir;
        p.StartInfo.RedirectStandardOutput = true;
        p.StartInfo.RedirectStandardError = true;
        p.StartInfo.RedirectStandardInput = true;
        p.OutputDataReceived += (object sender, DataReceivedEventArgs e) =>
        {
            Console.WriteLine(e.Data);
        };
        p.ErrorDataReceived += (object sender, DataReceivedEventArgs e) =>
        {
            Console.WriteLine(e.Data,"ERROR:");
        };
        p.Start();
        p.BeginErrorReadLine();
        p.BeginErrorReadLine();
        if (wait)
        {
            p.WaitForExit();
            int code = p.ExitCode;
            p.Close();

            Console.WriteLine(cmdExe + " exe return code: " + code);
            return code == 0;
        }
        return runSuc;
    }
}
