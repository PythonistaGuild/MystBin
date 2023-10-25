import * as React from "react"
const LoadingBall = (props) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width={200}
        height={200}
        preserveAspectRatio="xMidYMid"
        style={{
            margin: "auto",
            background: "0 0",
            display: "block",
            shapeRendering: "auto",
            fill: "currentColor"
        }}
        viewBox="0 0 100 100"
        {...props}
    >
        <circle cx={27} cy={50} r={23} fill="currentColor">
            <animate
                attributeName="cx"
                begin="-0.5s"
                dur="1s"
                keyTimes="0;0.5;1"
                repeatCount="indefinite"
                values="27;73;27"
            />
        </circle>
        <circle cx={73} cy={50} r={23} fill="currentColor" style={{filter: "brightness(90%)"}}>
            <animate
                attributeName="cx"
                begin="0s"
                dur="1s"
                keyTimes="0;0.5;1"
                repeatCount="indefinite"
                values="27;73;27"
            />
        </circle>
        <circle cx={27} cy={50} r={23} fill="currentColor">
            <animate
                attributeName="cx"
                begin="-0.5s"
                dur="1s"
                keyTimes="0;0.5;1"
                repeatCount="indefinite"
                values="27;73;27"
            />
            <animate
                attributeName="fill-opacity"
                calcMode="discrete"
                dur="1s"
                keyTimes="0;0.499;0.5;1"
                repeatCount="indefinite"
                values="0;0;1;1"
            />
        </circle>
    </svg>
)
export default LoadingBall
