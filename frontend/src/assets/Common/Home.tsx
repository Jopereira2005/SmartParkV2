import type { SVGProps } from 'react';

export function HomeIcon(props: SVGProps<SVGSVGElement>) {
	return (<svg
    width="1em"
    height="1em"
    viewBox="0 0 26 26"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M23.5 10.6162V23.5H18.125V19.1504C18.1249 18.2681 17.8016 17.4143 17.2139 16.7549L17.0928 16.625L16.9648 16.502C16.313 15.9025 15.4578 15.5635 14.5625 15.5635H11.4375C10.4825 15.5635 9.5728 15.9489 8.90723 16.625C8.24278 17.3 7.8751 18.2092 7.875 19.1504V23.5H2.5V10.6162L13 2.61719L23.5 10.6162Z"
      fill="currentColor"
      stroke="currentColor"
      strokeWidth={4}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>);
}