package bench.nativecompat;

import com.oracle.svm.core.annotate.Alias;
import com.oracle.svm.core.annotate.Substitute;
import com.oracle.svm.core.annotate.TargetClass;
import com.commercetools.internal.shaded.io.netty.channel.ChannelHandler;
import com.commercetools.internal.shaded.io.netty.channel.ChannelHandlerContext;
import com.commercetools.internal.shaded.io.netty.channel.embedded.EmbeddedChannel;
import com.commercetools.internal.shaded.io.netty.handler.codec.compression.*;
import static com.commercetools.internal.shaded.io.netty.handler.codec.http.HttpHeaderValues.*;

/** Preserve the installed HTTP decoders while removing an absent optional Zstd reference. */
@TargetClass(className = "com.commercetools.internal.shaded.io.netty.handler.codec.http.HttpContentDecompressor", onlyWith = AbsentOptionalBackends.Zstd.class)
final class CommerceContentDecoder {
    @Alias private boolean strict;
    @Alias private int maxAllocation;

    @Substitute
    protected EmbeddedChannel newContentDecoder(String encoding) throws Exception {
        ChannelHandler decoder;
        if (GZIP.contentEqualsIgnoreCase(encoding) || X_GZIP.contentEqualsIgnoreCase(encoding))
            decoder=ZlibCodecFactory.newZlibDecoder(ZlibWrapper.GZIP,maxAllocation);
        else if (DEFLATE.contentEqualsIgnoreCase(encoding) || X_DEFLATE.contentEqualsIgnoreCase(encoding))
            decoder=ZlibCodecFactory.newZlibDecoder(strict ? ZlibWrapper.ZLIB : ZlibWrapper.ZLIB_OR_NONE,maxAllocation);
        else if (Brotli.isAvailable() && BR.contentEqualsIgnoreCase(encoding))
            decoder=BrotliDecoder.newDecoderWithMaxAllocation(maxAllocation);
        else if (SNAPPY.contentEqualsIgnoreCase(encoding)) decoder=new SnappyFrameDecoder();
        else return null;
        var channel=((CommerceDecoderContext)(Object)this).ctx.channel();
        return EmbeddedChannel.builder().channelId(channel.id()).hasDisconnect(channel.metadata().hasDisconnect())
                .config(channel.config()).handlers(decoder).build();
    }
}

@TargetClass(className = "com.commercetools.internal.shaded.io.netty.handler.codec.http.HttpContentDecoder", onlyWith = AbsentOptionalBackends.Zstd.class)
final class CommerceDecoderContext {
    @Alias protected ChannelHandlerContext ctx;
}
