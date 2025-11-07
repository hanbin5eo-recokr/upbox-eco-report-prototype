#!/bin/bash

# pgrep을 사용해 "streamlit run" 프로세스가 실행 중인지 확인
if ! pgrep -f "streamlit run" > /dev/null
then
    echo "Streamlit is not running. Restarting..."
    # 가상환경 활성화 및 streamlit 실행 (절대 경로 사용)
    # 로그는 파일로 리다이렉션
    source /home/ec2-user/upbox-eco-report-prototype/.venv/bin/activate
    nohup streamlit run /home/ec2-user/upbox-eco-report-prototype/app.py --server.port 8501 > /home/ec2-user/applogs/streamlit.log 2>&1 &
fi
