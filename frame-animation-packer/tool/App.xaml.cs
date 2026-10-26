using System;
using System.Collections.Generic;
using System.Configuration;
using System.Data;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;

namespace FrameAnimeExportor
{
    /// <summary>
    /// App.xaml 的交互逻辑
    /// </summary>
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e) {
            base.OnStartup(e);
            if (e.Args.Length == 0) {
                new MainWindow().Show();
                return;
            }
            ShutdownMode = ShutdownMode.OnExplicitShutdown;
            Shutdown(AnimationBatch.Run(e.Args));
        }
    }
}
