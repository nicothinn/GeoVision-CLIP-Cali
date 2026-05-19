"use client";
import dynamic from "next/dynamic";

const MiniMapInner = dynamic(() => import("./MiniMapInner"), { ssr: false });
export { MiniMapInner };
export default MiniMapInner;
