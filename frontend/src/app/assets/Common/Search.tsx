import type { SVGProps } from 'react';

export function SearchIcon(props: SVGProps<SVGSVGElement>) {
	return (<svg
    width="1em"
    height="1em"
    viewBox="0 0 27 27"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M25.2421 25.5L20.0845 20.3424"
      stroke="currentColor"
      strokeWidth={3}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M12.2188 2C17.7201 2 22.1805 6.45963 22.1807 11.9609C22.1807 17.4624 17.7202 21.9229 12.2188 21.9229C6.71744 21.9226 2.25781 17.4623 2.25781 11.9609C2.25802 6.45976 6.71757 2.00021 12.2188 2Z"
      fill="currentColor"
      stroke="currentColor"
      strokeWidth={3}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>);
}