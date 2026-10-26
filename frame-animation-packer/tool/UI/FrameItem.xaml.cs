using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace FrameAnimeExportor.UI
{
    /// <summary>
    /// FrameItem.xaml 的交互逻辑
    /// </summary>
    public partial class FrameItem : UserControl
    {
        private int frameIndex;

        public FrameItem()
        {
            InitializeComponent();
        }

        //设置序号
        public void SetIndex(int value)
        {
            frameIndex = value;
            txtIndex.Text = frameIndex + "";
            MainControl.ins.SetFocusFrameHandler(OnFocusUpdate);
        }

        //设置时长
        public void SetDuration(int value)
        {
            txtDuration.Text = value + "";
        }

        private void txtDuration_KeyUp(object sender, System.Windows.Input.KeyEventArgs e)
        {
            if (e.Key != Key.Enter)
            {
                return;
            }
            MainControl.ins.SetDuration(frameIndex, int.Parse(txtDuration.Text));
        }

        private void StackPanel_MouseUp(object sender, MouseButtonEventArgs e)
        {
            MainControl.ins.MouseDownFrame(frameIndex);
        }

        private void OnFocusUpdate()
        {
            panelBg.Background = new SolidColorBrush(frameIndex == MainControl.ins.curFocusIndex?Colors.Orange: Colors.Yellow);
        }

    }
}
