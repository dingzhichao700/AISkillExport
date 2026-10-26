using System;
using System.Collections.Generic;

namespace FrameAnimeExportor
{
    public class MainControl
    {
        private MainWindow mainView;

        /**当前选中第几帧*/
        public int curFocusIndex = -1;

        /**选择时间轴的帧item后的回调列表*/
        private List<Action> frameFocusActions;

        public static MainControl _ins;

        public static MainControl ins
        {
            get
            {
                if (_ins == null)
                {
                    _ins = new MainControl();
                }
                return _ins;
            }
        }

        public void SetMainView(MainWindow view)
        {
            mainView = view;
        }

        //设置某一帧的时长
        public void SetDuration(int index, int duration)
        {
            mainView.SetFrameDuration(index, duration);
        }

        //在某帧上按下
        public void MouseDownFrame(int index)
        {
            SetFocusFrame(index);
        }

        /// <summary>
        /// 选中某帧
        /// </summary>
        /// <param name="index">帧索引，从1开始，0表示不选中任何帧</param>
        public void SetFocusFrame(int index)
        {
            if (curFocusIndex != index)
            {
                curFocusIndex = index;
                if (frameFocusActions != null)
                {
                    for (int i = 0; i < frameFocusActions.Count; i++)
                    {
                        frameFocusActions[i].Invoke();
                    }
                }
                mainView.MouseDownFrame(index);
            }
        }

        //设置选中某一帧后的回调
        public void SetFocusFrameHandler(Action action)
        {
            if (frameFocusActions == null)
            {
                frameFocusActions = new List<Action>();
            }
            frameFocusActions.Add(action);
        }

        public bool IsLoop()
        {
            return mainView.IsLoop();
        }

    }


}
